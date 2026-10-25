// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

//! Native checksum implementations for `smithy_checksums`.
//!
//! Each class mirrors the pure-Python implementation of the same name in
//! `smithy_checksums._private.crc`, so the two are interchangeable.

use std::sync::{Mutex, MutexGuard};

use pyo3::buffer::PyBuffer;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

/// Inputs at least this large are hashed with the interpreter detached so
/// other threads can run. Below it, detaching costs more than it saves. This
/// matches the threshold `hashlib` uses.
const DETACH_THRESHOLD: usize = 2048;

/// Streaming checksum state shared by every class in this module.
trait State: Clone + Send {
    fn new() -> Self;
    fn update(&mut self, data: &[u8]);
    fn digest(&self) -> Vec<u8>;
}

macro_rules! crc_state {
    ($state:ident, $algorithm:ident, $size:literal) => {
        #[derive(Clone)]
        struct $state(crc_fast::Digest);

        impl State for $state {
            fn new() -> Self {
                Self(crc_fast::Digest::new(crc_fast::CrcAlgorithm::$algorithm))
            }

            fn update(&mut self, data: &[u8]) {
                self.0.update(data);
            }

            fn digest(&self) -> Vec<u8> {
                // The digest is a u64 regardless of the CRC's width.
                self.0.finalize().to_be_bytes()[8 - $size..].to_vec()
            }
        }
    };
}

crc_state!(Crc32State, Crc32IsoHdlc, 4);
crc_state!(Crc32cState, Crc32Iscsi, 4);

fn lock<S>(state: &Mutex<S>) -> MutexGuard<'_, S> {
    // A panic while holding the lock can't leave a checksum half-updated in a
    // way that matters more than the panic itself, so ignore poisoning.
    state
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

/// Feeds the bytes of `data` to `state`.
///
/// `bytes` and other read-only buffers are hashed in place. Writable buffers
/// (such as `bytearray`) are copied first, because another thread could
/// otherwise modify them while they're being read.
fn update<S: State>(py: Python<'_>, state: &Mutex<S>, data: &Bound<'_, PyAny>) -> PyResult<()> {
    if let Ok(bytes) = data.cast::<PyBytes>() {
        hash_slice(py, state, bytes.as_bytes());
        return Ok(());
    }

    let buffer = PyBuffer::<u8>::get(data)?;
    if buffer.readonly() && buffer.is_c_contiguous() {
        // SAFETY: the buffer is read-only and C-contiguous, and `buffer`
        // keeps the exporter alive and its memory pinned until it's dropped
        // at the end of this function.
        let slice = unsafe {
            std::slice::from_raw_parts(buffer.buf_ptr().cast::<u8>(), buffer.len_bytes())
        };
        hash_slice(py, state, slice);
    } else {
        let copy = buffer.to_vec(py)?;
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
                PyBytes::new(py, &lock(&self.state).digest())
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

#[pymodule]
mod _native {
    #[pymodule_export]
    use super::{Crc32, Crc32C};
}
