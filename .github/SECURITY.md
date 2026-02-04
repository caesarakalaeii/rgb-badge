# Security Policy

## Supported Versions

This section outlines which versions of the RGB Badge project are currently supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| Latest development (main branch) | :white_check_mark: |
| Previous releases | :x: |

**Note:** As this is an active development hardware project, we focus security support on the latest version.

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in the RGB Badge project, please report it responsibly.

### What Constitutes a Security Issue?

For this hardware project, security issues might include:

- **Firmware vulnerabilities** that could allow unauthorized access or control
- **Power management issues** that could cause safety hazards (overheating, fire risk)
- **Hardware design flaws** that present electrical safety concerns
- **Supply chain concerns** with documented malicious components
- **Data handling issues** in firmware (if applicable to future features)

### How to Report

**Please DO NOT open a public issue for security vulnerabilities.**

Instead, please report security vulnerabilities via one of these methods:

1. **GitHub Security Advisories (Preferred)**
   - Navigate to the Security tab of this repository
   - Click "Report a vulnerability"
   - Fill out the advisory form with details

2. **Email** (if GitHub advisories are not available)
   - Send details to the project maintainers
   - Include "SECURITY" in the subject line
   - Provide detailed information about the vulnerability

### What to Include

When reporting a vulnerability, please include:

- **Description** of the vulnerability
- **Component affected** (firmware, PCB design, power system, etc.)
- **Steps to reproduce** the issue
- **Potential impact** and severity assessment
- **Suggested mitigation** (if you have ideas)
- **Affected versions** (if known)
- **Your contact information** (for follow-up)

### Response Timeline

- **Initial response:** Within 48-72 hours
- **Status update:** Within 1 week
- **Fix timeline:** Depends on severity and complexity

### Disclosure Policy

- We follow coordinated disclosure principles
- We'll work with you to understand and address the issue
- We'll credit you in the security advisory (unless you prefer to remain anonymous)
- We'll publish advisories after fixes are available
- Please allow reasonable time for fixes before public disclosure

## Security Best Practices

### For Users/Builders

- **Use proper power sources** - only use USB-C PD powerbanks rated for the required wattage
- **Inspect hardware** - check for shorts, damaged components before powering on
- **Follow assembly guidelines** - improper assembly can create safety hazards
- **Monitor temperature** - disconnect if components get excessively hot
- **Respect current limits** - do not modify firmware to exceed safe power limits

### For Contributors

- **Code review** - all firmware changes should be reviewed for security implications
- **Power limits** - maintain brightness caps and never remove power safety limits
- **Input validation** - validate any external input in firmware
- **Safe defaults** - design should fail safely (e.g., limiting power on error)
- **Documentation** - clearly document any safety-critical parameters

## Known Security Considerations

### Current Design

- **Power management:** Firmware includes brightness caps to prevent exceeding powerbank limits
- **Electrical safety:** Design follows standard PCB safety practices
- **Heat management:** Buck converter and high-current traces sized appropriately

### Potential Risks

- **User modification:** Removing firmware power limits could cause safety issues
- **Counterfeit components:** Using non-authentic parts may have different characteristics
- **Assembly errors:** Incorrect assembly could create shorts or safety hazards

## Compliance

This project follows:
- Standard PCB design safety practices
- USB-C and USB Power Delivery specifications
- Electronic assembly safety guidelines

## Contact

For security concerns that don't fit the above categories, or for questions about this security policy, please open a regular issue with the `security` label (for non-sensitive topics) or use the private reporting methods described above.

## Updates to This Policy

This security policy may be updated as the project evolves. Check back periodically for changes.

---

**Last Updated:** 2026-02-04
