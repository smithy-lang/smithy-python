// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

//! Native checksum implementations for `smithy_checksums`.
//!
//! Each class mirrors the pure-Python implementation of the same name in
//! `smithy_checksums._private.crc`, so the two are interchangeable.

use std::sync::{Mutex, MutexGuard};

use pyo3::buffer::PyBuffer;
use pyo3::types::{PyAny, PyBytes, PyBytesMethods};
use pyo3::{Bound, PyResult, Python, pyclass, pymethods, pymodule};

/// Inputs at least this large are hashed with the interpreter detached so
/// other threads can run. Below it, detaching costs more than it saves. This
/// matches the threshold `hashlib` uses.
const DETACH_THRESHOLD: usize = 2048;

/// Streaming checksum state shared by every class in this module.
trait State: Clone + Send {
    /// The digest, a byte array as long as the algorithm's output.
    type Digest: AsRef<[u8]>;

    fn new() -> Self;
    fn update(&mut self, data: &[u8]);
    fn digest(&self) -> Self::Digest;
}

macro_rules! crc_state {
    ($state:ident, $algorithm:ident, $width:ty) => {
        #[derive(Clone)]
        struct $state(crc_fast::Digest);

        impl State for $state {
            type Digest = [u8; size_of::<$width>()];

            fn new() -> Self {
                Self(crc_fast::Digest::new(crc_fast::CrcAlgorithm::$algorithm))
            }

            fn update(&mut self, data: &[u8]) {
                self.0.update(data);
            }

            fn digest(&self) -> Self::Digest {
                // `finalize` returns a u64 regardless of the CRC's width, and
                // the CRC is in its low bits.
                (self.0.finalize() as $width).to_be_bytes()
            }
        }
    };
}

crc_state!(Crc32State, Crc32IsoHdlc, u32);
crc_state!(Crc32cState, Crc32Iscsi, u32);
crc_state!(Crc64NvmeState, Crc64Nvme, u64);

fn lock<S>(state: &Mutex<S>) -> MutexGuard<'_, S> {
    // A panic while holding the lock can't leave a checksum half-updated in a
    // way that matters more than the panic itself, so ignore poisoning.
    state
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

/// Feeds the bytes of `data` to `state`.
///
/// `bytes` is immutable, so it's hashed in place. Other buffers are copied
/// first, because another thread could modify them while they're being read.
/// That includes read-only buffers: the flag only stops this reader from
/// writing, and a read-only `memoryview` of a `bytearray` can still change.
fn update<S: State>(py: Python<'_>, state: &Mutex<S>, data: &Bound<'_, PyAny>) -> PyResult<()> {
    if let Ok(data) = data.cast::<PyBytes>() {
        hash_slice(py, state, data.as_bytes());
    } else {
        let copy = PyBuffer::<u8>::get(data)?.to_vec(py)?;
        hash_slice(py, state, &copy);
    }
    Ok(())
}

fn hash_slice<S: State>(py: Python<'_>, state: &Mutex<S>, data: &[u8]) {
    if data.len() < DETACH_THRESHOLD {
        lock(state).update(data);
    } else {
        py.detach(|| lock(state).update(data));
    }
}

macro_rules! checksum_class {
    ($name:ident, $state:ident) => {
        #[pyclass(frozen, module = "smithy_checksums._native")]
        struct $name {
            state: Mutex<$state>,
        }

        #[pymethods]
        impl $name {
            #[new]
            fn new() -> Self {
                Self {
                    state: Mutex::new($state::new()),
                }
            }

            fn update(&self, py: Python<'_>, data: &Bound<'_, PyAny>) -> PyResult<()> {
                update(py, &self.state, data)
            }

            fn digest<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
                PyBytes::new(py, lock(&self.state).digest().as_ref())
            }

            fn copy(&self) -> Self {
                Self {
                    state: Mutex::new(lock(&self.state).clone()),
                }
            }
        }
    };
}

checksum_class!(Crc32, Crc32State);
checksum_class!(Crc32C, Crc32cState);
checksum_class!(Crc64Nvme, Crc64NvmeState);

#[pymodule]
mod _native {
    #[pymodule_export]
    use super::{Crc32, Crc32C, Crc64Nvme};
}
