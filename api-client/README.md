# API Client Generator

Auto-generated TypeScript client from OpenAPI specification.

## Usage

### Generate Client

```bash
cd api-client
npm install
npm run generate
```

### Copy to Frontend

After generation, copy the generated files to `frontend/src/api/`:

```bash
cp -r src/generated/* ../frontend/src/api/generated/
```

### Validate OpenAPI Spec

```bash
npm run validate
```

## Generated Files

- `src/generated/api/` - API client classes
- `src/generated/models/` - TypeScript interfaces

## Notes

- Generator uses `typescript-axios` by default
- Use `npm run generate:fetch` for fetch-based client
