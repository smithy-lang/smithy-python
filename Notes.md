## TODOs
1. We should look into whether services model response_metadata
2. Does Trebuchet validate this?
3. Is there guidance in any Seps, like Smithy specs

## Notes
- Applying changes to HttpBinding... interface will only get changes into REST protocols (not query or RPC)
- Should `ResponseMetadata` stuff be thrown in `smithy-http`? We generally try to throw aws-specific stuff into `smithy-aws-core`.
  - I could be convince if this made the implementation siginificantly simpler / more maintainable
