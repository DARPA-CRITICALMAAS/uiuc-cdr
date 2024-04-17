# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.1.0] - 2024-04-16

### Added
- if cdrhook fails, push message to cdrhook.error

### Changed
- uploaded will now load cdr json and add cog_id, system and system_version.

### Fixed
- timeout on ack for RabbitMQ is now 2 hours

## [0.0.7] - 2024-04-15

This is the inital release of the UIUC CDR Processing steps. The pipeline is in another git repository.
