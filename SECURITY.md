# Security Policy

## Supported Versions

We provide security updates for the following versions of Onix:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT create a public issue

**Do not** create a public GitHub issue for security vulnerabilities. This could potentially expose the vulnerability to malicious actors.

### 2. Report privately

Please report security vulnerabilities privately by:

- **Email**: [INSERT SECURITY EMAIL]
- **GitHub Security Advisory**: Use GitHub's private vulnerability reporting feature
- **Direct Message**: Contact the maintainer directly

### 3. Include the following information

When reporting a security vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Impact**: Potential impact of the vulnerability
- **Affected versions**: Which versions are affected
- **Proof of concept**: If available, include a proof of concept
- **Suggested fix**: If you have ideas for fixing the issue

### 4. Response timeline

We will respond to security vulnerability reports within:

- **Initial response**: 24-48 hours
- **Status update**: Within 1 week
- **Resolution**: As quickly as possible, typically within 30 days

### 5. Disclosure process

- We will work with you to understand and reproduce the vulnerability
- We will develop and test a fix
- We will coordinate the release of the fix
- We will publicly disclose the vulnerability after the fix is available

## Security Features

Onix includes several security features to protect your privacy and data:

### Connection Security
- **Kill Switch**: Automatic connection protection on proxy failure
- **DNS Leak Protection**: Prevent DNS leaks and ensure privacy
- **Certificate Pinning**: Enhanced security for TLS connections
- **IPv6 Leak Protection**: Comprehensive IPv6 leak prevention

### Privacy Controls
- **Data Collection Controls**: Disable telemetry, crash reports, and usage statistics
- **Logging Privacy**: Disable detailed logging and clear logs on exit
- **Network Privacy**: Disable DNS query logging and traffic statistics
- **Application Privacy**: Disable auto-updates and core auto-updates

### Security Settings
- **Connection Security**: IPv6 support, insecure connections, certificate verification
- **Advanced Security**: Custom CA certificates, cipher suites, security level
- **Connection Settings**: Connection timeout, retry attempts, keep-alive

## Best Practices

### For Users
- Keep Onix updated to the latest version
- Use strong, unique passwords for your proxy accounts
- Enable security features like Kill Switch and DNS Leak Protection
- Regularly check for updates
- Use trusted proxy providers
- Be cautious with configuration files from unknown sources

### For Developers
- Follow secure coding practices
- Keep dependencies updated
- Use secure communication channels
- Implement proper input validation
- Use secure random number generation
- Follow the principle of least privilege

## Security Updates

Security updates are released as soon as possible after a vulnerability is discovered and fixed. We recommend:

- Enabling automatic updates
- Regularly checking for updates
- Applying security updates immediately
- Testing updates in a safe environment before production use

## Contact

For security-related questions or concerns, please contact:

- **Security Email**: [INSERT SECURITY EMAIL]
- **GitHub Issues**: For non-security issues only
- **Discussions**: For general security questions

## Acknowledgments

We would like to thank the security researchers and community members who have helped improve Onix's security through responsible disclosure.

## License

This security policy is part of the Onix project and is subject to the same MIT License as the main project.
