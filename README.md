# Echotome
An audio to encryption app.

## Development

### Installation
```bash
npm install
```

### Development Server
```bash
npm run dev
```
This starts the development server at http://localhost:3000

### Build
```bash
npm run build
```
This creates a production build in the `dist/` directory.

### Preview Production Build
```bash
npm run preview
```

## Project Structure
- `src/main.ts` - Main application entry point
- `src/pdl.ts` - Proprietary Derivation Layer for cryptographic key derivation
- `src/guard.ts` - Security and integrity checking functions
- `src/styles.css` - Application styles
- `index.html` - Application HTML shell

