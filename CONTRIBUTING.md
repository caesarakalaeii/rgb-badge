# Contributing to RGB Badge

Thank you for your interest in contributing to the RGB Badge project! This document provides guidelines for contributing to this open-source hardware project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Design Guidelines](#design-guidelines)
- [Submitting Changes](#submitting-changes)
- [Hardware Testing](#hardware-testing)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Hardware version** (if applicable)
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Photos or screenshots** (if relevant)
- **Schematic/layout screenshots** (for PCB issues)
- **KiCad version** (for design files)

Use the bug report template when creating issues.

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear, descriptive title**
- **Provide detailed description** of the proposed feature
- **Explain why this would be useful** to most users
- **Consider impact on power consumption, cost, and manufacturability**

### Hardware Contributions

This is primarily a hardware project. Contributions can include:

- **PCB layout improvements** (signal integrity, power distribution, routing)
- **Schematic refinements** (component selection, circuit optimization)
- **BOM optimization** (cost reduction, alternative parts)
- **Firmware improvements** (LED driving, animations, performance)
- **Mechanical design** (enclosure, mounting, wearability)
- **Documentation** (assembly guides, datasheets, testing procedures)

### Documentation

Documentation improvements are always welcome:

- Fixing typos or clarifying existing docs
- Adding assembly instructions
- Creating build guides with photos
- Translating documentation
- Adding datasheets for components

## Development Setup

### Hardware Design

**Required tools:**
- [KiCad](https://www.kicad.org/) 7.0 or later
- Git for version control
- Text editor for documentation

**Recommended tools:**
- KiCad library manager for component libraries
- PDF viewer for datasheets
- Image editor for documentation photos

### Firmware Development

**Required tools:**
- [ESP-IDF](https://docs.espressif.com/projects/esp-idf/) or [Arduino IDE](https://www.arduino.cc/en/software)
- USB-C cable for programming
- Powerbank for power testing

**Setup steps:**
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/rgb-badge.git
cd rgb-badge

# Open KiCad project files
# (Navigate to PCB design directories)
```

## Design Guidelines

### PCB Design

1. **Layer stack:** Follow the documented layer stack in the design files
2. **Trace widths:** Adhere to power distribution guidelines (see README.md)
3. **Component placement:** Maintain specified LED pitch (1.5625×1.625mm)
4. **Decoupling:** Follow datasheet requirements for capacitor placement
5. **Signal integrity:** Keep data lane routing clean, use specified series resistors

### Schematic

1. **Annotations:** Use clear, descriptive component references
2. **Net names:** Use meaningful names for signals and power nets
3. **Documentation:** Add notes for critical design decisions
4. **Datasheets:** Link to datasheets in component properties

### Firmware

1. **Style:** Follow ESP-IDF or Arduino style guidelines
2. **Comments:** Document non-obvious logic, especially timing-critical code
3. **Power management:** Respect brightness caps and power limits
4. **Performance:** Maintain 60+ FPS target on all data lanes

### Testing Requirements

For hardware changes:
- Verify DRC passes in KiCad
- Check power distribution simulations
- Validate against manufacturer constraints (soldermask, drill sizes)
- Test with prototype if available

For firmware changes:
- Test on actual hardware if possible
- Verify refresh rate meets targets
- Check power consumption stays within limits
- Test multiple animation patterns

## Submitting Changes

### Pull Request Process

1. **Fork the repository** and create a branch from `main`
2. **Make your changes** following the guidelines above
3. **Test thoroughly** - see Testing Requirements
4. **Update documentation** - README, comments, datasheets as needed
5. **Commit with clear messages** - see Commit Guidelines
6. **Open a Pull Request** with description of changes

### Commit Guidelines

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Reference issues when applicable (#123)
- For hardware changes, mention affected boards/schematics

**Examples:**
```
Add decoupling capacitors to matrix PCB power rails

Fix level shifter footprint orientation on controller board

Update BOM with alternative buck converter options (#42)
```

### Pull Request Template

When opening a PR, include:
- **Summary** of changes
- **Motivation** - why is this change needed?
- **Testing** - how was it verified?
- **Photos/screenshots** (for hardware changes)
- **Breaking changes** - does this affect existing builds?
- **Related issues** - fixes #123

### Review Process

1. Maintainers will review your PR
2. Feedback may be provided - please be responsive
3. Changes may be requested
4. Once approved, a maintainer will merge

**Review criteria:**
- Design follows project guidelines
- Changes are well-documented
- Testing is adequate
- No regressions introduced
- Maintains AGPL-3.0 license compatibility

## Hardware Testing

### Prototype Testing

If you have access to hardware:

1. **Visual inspection** - check for shorts, tombstoning, solder quality
2. **Power-on test** - verify current draw, no smoke
3. **LED test** - test each data lane independently
4. **Refresh rate** - measure actual FPS achieved
5. **Thermal** - check for hot spots during operation
6. **Mechanical** - verify fit, mounting, wearability

### Simulation Testing

For changes without hardware access:

1. **KiCad DRC** - must pass without errors
2. **Power distribution** - verify voltage drops acceptable
3. **Signal integrity** - check trace impedance, timing margins
4. **Thermal simulation** - estimate temperatures for critical components

## Questions?

- Open an issue with the `question` label
- Check existing documentation and issues first
- Be specific about what you need help with

## Recognition

Contributors will be recognized in:
- Git commit history
- Release notes for significant contributions
- README contributors section (optional)

Thank you for contributing to making this project better!

---

**License:** By contributing, you agree that your contributions will be licensed under the GNU AGPL-3.0 license.
