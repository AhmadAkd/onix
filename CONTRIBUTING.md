# Contributing to Onix

We welcome contributions to Onix! To ensure a smooth and collaborative development process, please follow these guidelines. Any contribution, whether it's a bug report, a new feature, or a documentation improvement, is greatly appreciated.

## Recent Updates (v1.1.0)

Onix has recently received major updates including:
- Enhanced Settings UI with Security, Performance, and Privacy tabs
- Real-time Speed Test functionality
- Auto-failover and improved Health Check
- Advanced Security features (Kill Switch, DNS Leak Protection)
- Real-time Statistics and Monitoring
- Custom Themes and improved RTL support
- Comprehensive Privacy Controls
- Performance Analytics and Diagnostics
- Browser Integration and Keyboard Shortcuts
- Multi-user Support and Auto-backup

These new features provide a solid foundation for future contributions and improvements.

## How to Contribute

### Reporting Bugs

If you find a bug, please [open an issue](https://github.com/AhmadAkd/onix/issues) on GitHub. Provide as much detail as possible, including:

- A clear and concise description of the bug.
- Steps to reproduce the behavior.
- Expected behavior.
- Screenshots or error messages (if applicable).
- Your operating system and Onix version.

### Feature Requests

We welcome ideas for new features! Please [open an issue](https://github.com/AhmadAkd/onix/issues) to suggest new features. Describe:

- The problem your feature solves.
- How you envision the feature working.
- Any potential benefits or use cases.

### Submitting Changes

1. **Fork the Repository:** Start by forking the Onix repository to your GitHub account.
2. **Clone Your Fork:** Clone your forked repository to your local machine.

    ```bash
    git clone https://github.com/YOUR-USERNAME/onix.git
    cd onix
    ```

3. **Create a New Branch:** Create a new branch for your feature or bug fix. Use a descriptive name (e.g., `feature/add-new-protocol`, `bugfix/connection-issue`).

    ```bash
    git checkout -b feature/your-feature-name
    ```

4. **Make Your Changes:** Implement your changes, ensuring they adhere to the project's coding style and conventions.
5. **Test Your Changes:** Thoroughly test your changes to ensure they work as expected and do not introduce new bugs. If applicable, add new unit tests.
6. **Commit Your Changes:** Write clear and concise commit messages. Follow the **Commit Message Convention** described below.

    ```bash
    git commit -m "feat: Briefly describe your changes"
    ```

7. **Push to Your Fork:** Push your local branch to your forked repository on GitHub.

    ```bash
    git push origin feature/your-feature-name
    ```

8. **Create a Pull Request (PR):** Go to the original Onix repository on GitHub and create a new Pull Request from your forked branch.
    - Provide a clear title and detailed description of your changes.
    - Reference any related issues (e.g., `Closes #123`).
    - Ensure your PR passes all CI checks.

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code style.
- Use clear and descriptive variable/function names.
- Add comments where necessary to explain complex logic.

### Commit Message Convention

We use the **Conventional Commits** specification for our commit messages. This leads to more readable messages that are easy to follow and allows us to automate the generation of changelogs.

Each commit message should be structured as follows:

```
<type>(<scope>): <subject>
```

**Type**

The type must be one of the following:

- **feat**: A new feature for the user.
- **fix**: A bug fix for the user.
- **docs**: Changes to documentation.
- **style**: Code style changes (formatting, white-space, etc.).
- **refactor**: A code change that neither fixes a bug nor adds a feature.
- **perf**: A code change that improves performance.
- **test**: Adding missing tests or correcting existing tests.
- **build**: Changes that affect the build system or external dependencies.
- **ci**: Changes to our CI configuration files and scripts.
- **chore**: Other changes that don't modify source or test files.

**Examples**

- `feat(ui): Add a new 'About' window`
- `fix(proxy): Correctly handle system proxy disabling on exit`
- `docs: Update contribution guidelines with commit conventions`
- `refactor(settings): Simplify settings loading logic`
- `ci: Automate changelog generation on release`
