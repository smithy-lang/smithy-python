# Change Log

## Unreleased

### Breaking Changes

* Removed the `http_client` config option in favor of the generic `transport`.

### Features

* Removed code-generated protocol implementations in favor of hand-written
  implementations based on schemas.
* Moved documentation for structure members into doc strings after the member's
  dataclass field declaration.
