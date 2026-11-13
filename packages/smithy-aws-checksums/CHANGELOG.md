# Changelog

## v0.1.1

### Enhancements
* Added docstrings to the public API and ordered public definitions first.

## v0.1.0

### Features
* Added XXHash64, XXHash3, and XXHash128 checksums.
* Added CRC64NVME checksums.
* Added CRC32 and CRC32C checksums, backed by a native Rust extension with a pure-Python fallback, and SHA-1, SHA-256, SHA-512, and MD5 checksums through `new()`.
