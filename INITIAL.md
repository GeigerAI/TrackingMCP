## FEATURE:
- MCP Server that enable Pydantic AI agents to track packages with FedEx or UPS API
- Setup for both local and cloud LLMs
- Requirements for input into the MCP are carrier and tracking number
- 


## EXAMPLES:

In the `examples/` folder, there is a README for you to read to understand what the example is all about and also how to structure your own README when you create documentation for the above feature.

- `examples/fedex_oauth.py` - use this as a template to get OAuth tokens for FedEx
- `examples/fedex_tracking.py` - use this as a template to get tracking results for a FedEx shipment
- `examples/ups_tracking.py` - use this as a template to get tracking results for a UPS shipment
- `examples/ups_oauth_token.py` - use this as a template to get OAuth tokens for UPS



## DOCUMENTATION:

Pydantic AI documentation: https://ai.pydantic.dev/
Example MCP Server: https://github.com/coleam00/mcp-mem0
FedEx Tracking API: https://developer.fedex.com/api/en-us/catalog/track/v1/docs.html
FedEx OAuth: https://developer.fedex.com/api/en-ca/catalog/authorization/v1/docs.html
UPS OAuth: https://developer.ups.com/tag/OAuth-Auth-Code?loc=en_US&tag=Tracking#operation/GenerateToken



## OTHER CONSIDERATIONS:

- Include a .env.example, README with instructions for setup including how to configure Gmail and Brave.
- Include the project structure in the README.
- Virtual environment has already been set up with the necessary dependencies.
- Use python_dotenv and load_env() for environment variables
