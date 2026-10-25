# smithy-checksums

This package provides the checksum algorithms used by Smithy clients: CRC32 and
CRC32C, and, through `new()`, SHA-1, SHA-256, SHA-512, and MD5.

```python
import smithy_checksums

checksum = smithy_checksums.new("CRC32C")
checksum.update(b"hello world")
checksum.digest()
```

## Native acceleration

The CRC algorithms are implemented in Rust and published as wheels for
common platforms. Where no wheel is available, the package installs as pure Python
and produces identical results, much more slowly. `HAS_NATIVE_EXTENSION` reports
which implementation is in use. CRC32 always uses `zlib` in pure Python, and the
SHA and MD5 algorithms always use `hashlib`.

## Building

Wheels are built with [maturin](https://www.maturin.rs/) when `cargo` is on the
`PATH`, and as pure Python when no Rust toolchain is installed. If Rust is installed
but can't build the extension, for example because it's older than the
`rust-version` in `Cargo.toml`, the build fails with instructions instead of
silently falling back.

Set `SMITHY_PYTHON_NATIVE_BUILD` to `never` to build a pure-Python wheel, or to
`always` to require the native extension even when `cargo` isn't on the `PATH`.
