1. **Null Safety**: ALWAYS prefer `java.util.Optional` (e.g., `Optional.ofNullable(...)`) for handling potential null objects or variables. Do NOT blindly assign default primitive values (like 0 or "") unless contextually required.
2. **Parameter Validation**: If a method parameter is null and shouldn't be, use `java.util.Objects.requireNonNull()` rather than manual if/else blocks.
3. **Fail-Fast**: Never catch NullPointerException. Fix the root cause instead.
4. **Modern Java**: Use Java 21 features where appropriate (Pattern matching, records, etc.).
5. **Immutability**: Prefer `final` keywords for variables that should not be reassigned.