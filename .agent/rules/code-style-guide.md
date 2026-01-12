---
trigger: always_on
---

## Project Rules & Expectations

This project is **strictly for learning purposes**, with an emphasis on **production-quality practices**.

### Background Context

I have a prior background in the **MERN stack and Next.js**, and I am now learning:

- **Flask** (Python backend framework)
- **PostgreSQL** (relational database)

The goal is to build a **backend server** while deeply understanding _how things work_, not just making them work.

---

### Teaching & Explanation Style

- Assume I may ask **very basic or cross-questions**, including:

  - What a method does
  - Why it exists
  - How it works internally
  - How data flows through the system

- All explanations must be:

  - **Simple**
  - **Very detailed**
  - **Step-by-step**

- Explanations should help me:

  - Visualize the data flow
  - Understand the execution flow clearly

---

### Documentation Requirements

- Maintain **Markdown (`.md`) documentation** inside a `docs/` folder.
- These documents will act as my **personal notes** for future reference.
- Documentation must:

  - Explain _what was implemented_
  - Explain _why it was implemented_
  - Explain _how it works internally_

- Use:

  - Diagrams (ASCII diagrams, Mermaid diagrams, or similar) wherever helpful

- You may create **subdirectories inside `docs/`** as needed to keep things organized and easy to navigate.

---

### Project Setup & Tooling

You must help me with:

- Setting up the project from scratch
- Adding and configuring libraries, such as:

  - Input validation libraries (Node equivalents like `zod` / `joi`, but for Flask/Python)
  - API documentation tools (e.g., Swagger / OpenAPI)
  - Any other commonly used backend tooling

- For every major setup or integration:

  - Create a corresponding `.md` file in the `docs/` folder
  - Explain configuration decisions and trade-offs

---

### Code Requirements

- Generate **production-quality code**

  - Clean
  - Readable
  - Maintainable

- Code should be:

  - **Atomic**
  - **Modular**
  - **Reusable**

- Follow best practices commonly used in real-world production systems.
- Assume the code _could be directly deployed_ to production with minimal changes.

---

### Explanation After Code

For every implementation:

1. Explain **what was done**
2. Explain **why it was done this way**
3. Explain the **full flow**, including:

   - Request lifecycle
   - Data validation
   - Business logic
   - Database interaction
   - Response generation

---

### Overall Goal

This project should help me:

- Learn Flask and PostgreSQL deeply
- Build a strong mental model of backend architecture
- Accumulate high-quality documentation that I can revisit later
- Transition confidently from Node.js to Python backend development
