import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";
import pluginSecurity from "eslint-plugin-security";

/** @type {import('eslint').Linter.Config[]} */
const config = [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...tseslint.configs.strict,
  ...pluginVue.configs["flat/recommended"],
  pluginSecurity.configs.recommended,
  {
    files: ["**/*.{ts,vue}"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
    rules: {
      // ==============================================================================
      // TypeScript - Strict Mode (Practical)
      // ==============================================================================
      "@typescript-eslint/no-unused-vars": ["warn", {
        "argsIgnorePattern": "^_|^index$",
        "varsIgnorePattern": "^_|^error$|^e$|^err$|parseError|DEFAULT_"
      }],
      "no-case-declarations": "off",  // Allow let/const in case blocks
      "@typescript-eslint/no-empty-object-type": "off",
      "@typescript-eslint/no-explicit-any": "warn",  // Warn, not error - gradual improvement
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/no-non-null-assertion": "off",  // Common pattern with optional chaining
      "@typescript-eslint/no-floating-promises": "off",
      "@typescript-eslint/no-unnecessary-condition": "off",
      "@typescript-eslint/prefer-nullish-coalescing": "off",
      "@typescript-eslint/no-confusing-void-expression": "off",
      "@typescript-eslint/no-invalid-void-type": "off",
      "@typescript-eslint/restrict-template-expressions": "off",
      "@typescript-eslint/no-dynamic-delete": "off",
      "@typescript-eslint/ban-ts-comment": "off",

      // ==============================================================================
      // Vue - Security Focused
      // ==============================================================================
      "vue/multi-word-component-names": "off",
      "vue/no-v-html": "warn",  // Warn for XSS risk (some components need this)
      "vue/no-v-text-v-html-on-component": "warn",
      "vue/require-default-prop": "off",
      "vue/html-self-closing": ["warn", {
        "html": { "void": "always", "normal": "never", "component": "always" },
        "svg": "always",
        "math": "always"
      }],
      "vue/max-attributes-per-line": ["warn", {
        "singleline": 5,
        "multiline": 1
      }],
      "vue/singleline-html-element-content-newline": "off",

      // ==============================================================================
      // Security Rules - Important (Warnings for gradual improvement)
      // ==============================================================================
      "security/detect-object-injection": "off",  // Too many false positives
      "security/detect-non-literal-regexp": "warn",
      "security/detect-unsafe-regex": "warn",  // May have false positives
      "security/detect-eval-with-expression": "error",
      "security/detect-no-csrf-before-method-override": "off",
      "security/detect-buffer-noassert": "error",
      "security/detect-child-process": "warn",
      "security/detect-disable-mustache-escape": "error",
      "security/detect-new-buffer": "error",
      "security/detect-possible-timing-attacks": "off",  // Too many false positives
      "security/detect-pseudoRandomBytes": "warn",

      // ==============================================================================
      // General - Code Quality
      // ==============================================================================
      "no-console": ["warn", { "allow": ["warn", "error"] }],  // Warn, not error
      "no-debugger": "error",
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "no-script-url": "off",  // We handle this in security utils
      "no-undef": "off",  // TypeScript handles this
      "prefer-const": "error",
      "no-var": "error",
      "eqeqeq": ["error", "always", { "null": "ignore" }],
      "no-alert": "error",
      "no-return-assign": "error",
      "no-sequences": "error",
      "no-throw-literal": "error",
      "no-unused-expressions": ["error", { "allowShortCircuit": true }],
      "radix": "off",  // parseInt without radix is common pattern
      "no-async-promise-executor": "off",  // Allow async promise executors
      "@typescript-eslint/no-extraneous-class": "off",  // Allow utility classes
    },
  },
  {
    // Test files - relaxed rules
    files: ["**/*.spec.ts", "**/*.test.ts", "**/tests/**/*.ts"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "security/detect-object-injection": "off",
    },
  },
  {
    ignores: ["dist/**", "node_modules/**", "*.config.js", "*.config.ts", "coverage/**"],
  },
];

export default config;
