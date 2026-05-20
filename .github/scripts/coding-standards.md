{
"target_exceptions": [
"java.lang.NullPointerException",
"java.lang.ClassCastException",
"java.lang.IndexOutOfBoundsException",
"java.lang.IllegalArgumentException"
],
"spring_di_rules": [
"UnsatisfiedDependencyException: Look for missing @Service, @Component, or @Repository annotations on the required bean.",
"NoSuchBeanDefinitionException: The required bean is not defined or component scanning is missing it.",
"NoUniqueBeanDefinitionException: Multiple beans of the same type exist. Fix by using @Qualifier or @Primary.",
"BeanCreationException: Often caused by missing configuration properties or failing constructor logic. Check for @Value annotations or missing environment variables."
]
}