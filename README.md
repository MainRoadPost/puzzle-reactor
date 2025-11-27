# Puzzle Reactor

An example reactor application that interacts with the Puzzle API using GraphQL queries and WebSocket subscriptions.

## Description

This demo application shows how to:

1. **Connect to the Puzzle API** — authenticate a user through GraphQL
2. **Fetch data** — retrieve a list of active projects via GraphQL queries
3. **Monitor real-time updates** — use WebSocket subscriptions to track updates:
   - `onProjectsUpdated` — watches for project changes
   - `onProductsUpdated` — watches for product changes

The application demonstrates a reactive approach to working with Puzzle data, where updates arrive automatically through a WebSocket connection without polling the API.

## Changing the generated client code

The project uses a generated client (the `puzzle` module) created by the **ariadne-codegen** tool to interact with the Puzzle GraphQL API. If you need to change the client functionality, do not modify the generated `puzzle` module directly.

Instead:

1. Ensure `schema.graphql` contains the current data model.
2. Update `queries.graphql` to include the queries you need for the Puzzle backend.
3. Regenerate the `puzzle` module by running:

   ```bash
   uv run ariadne-codegen
   ```

**Important:** Running `ariadne-codegen` is required before the first run of the application and after any changes to `schema.graphql` or `queries.graphql`.

## Updating the GraphQL schema

To update the schema you need the `cynic-cli` tool, which can be installed using Cargo. ([Rust language](https://rust-lang.org/tools/install) must be installed on your system)

```shell
cargo install --git https://github.com/obmarg/cynic.git cynic-cli
```

After installing `cynic-cli`, run the `get-schema.sh` script at the repository root to download the current GraphQL schema to `schema.graphql`:

```shell
./get-schema.sh > schema.graphql
```

The script authenticates with the Puzzle server and saves the resulting schema to `schema.graphql`.

Before running the script, ensure the following `.env` variables are set:
- `PUZZLE_API` — the Puzzle GraphQL API URL.
- `PUZZLE_USER_DOMAIN` — studio domain (leave empty if not used).
- `PUZZLE_USERNAME` — the username.
- `PUZZLE_PASSWORD` — the password.

An example `.env` file is provided in `example.env`.