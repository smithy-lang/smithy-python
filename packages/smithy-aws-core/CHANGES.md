# Changelog

## Unreleased

* _Add new items here_

### Breaking Changes

* Updated sigv4 auth resolution and identity providers to the new transport-
  agnostic interfaces.

### Features

* Added a hand-written implmentation for the `restJson1` protocol.

## v0.0.3

### Bugfixes
* Rename `ContainerCredentialResolver` to `ContainerCredentialsResolver` to
  match new naming standard.

## v0.0.2

### Feature
* Added support for Container credential resolution, commonly used with ECS/EKS.

## v0.0.1

### Features

* Added support for Instance Metadata Service (IMDS) credential resolution.
* Added basic endpoint support.
* Added basic User Agent support.
* Added basic AWS specific protocol support for RestJson1 and HTTP bindings.
