# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.4.0] - 2024-04-26

### Added
- can now set a prefix for all queue names (PREFIX="")

### Changed
- renamed server folder to cdrhook
- monitor shows number of messages processing, "61 / 1" means 61 messages waiting, 1 being processed

## [0.3.0] - 2024-04-23

### Added
- limit uploads to 300Mb by default (MAX_SIZE=300)

## [0.2.0] - 2024-04-23

### Added
- can record unknown events in rabbitmq (CDR_KEEP_EVENT=yes)
- monitor number of unknown events from cdrhook

### Changed
- docker-compose file now uses latest tag

### Fixed
- fixed error in uploaded with getting value from dict

## [0.1.0] - 2024-04-16

### Added
- if cdrhook fails, push message to cdrhook.error

### Changed
- uploaded will now load cdr json and add cog_id, system and system_version.

### Fixed
- timeout on ack for RabbitMQ is now 2 hours

## [0.0.7] - 2024-04-15

This is the inital release of the UIUC CDR Processing steps. The pipeline is in another git repository.
