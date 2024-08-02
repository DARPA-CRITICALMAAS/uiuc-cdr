# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added 
- Added connection and retrieve api for CDR interface
- Added support for downloading legends from the CDR
- Added unittests for cdrhook process_cog code
- Added pytest github action
- Added linting github action
- File `systems.json` controls order to check for map_area and polygon_legent

### Changed
- Updated cdrhook server code
- Updated message interface for download queue "map_area" -> "map_data"
- cdrhook has default log level of INFO (can be changed with LOGLEVEL environment variable)


## [0.7.3] - 2024-05-13

### Added
- Added conditional wait to combat potential parallel file system race condition when pipeline components are all running synchronously.  Only waits when file that should exist doesn't exist.  

## [0.7.2] - 2024-05-03

### Fixed
- remove debug message

## [0.7.1] - 2024-05-03

### Changed
- set version number in docker based on tag

## [0.7.0] - 2024-05-03

### Fixed
- cdrhook: restart rabbitmq listener in case of error
- cdrhook: in case of exception processing event move to error queue
- cdrhook: strip whitespaces from event id

## [0.6.0] - 2024-05-01

### Added
- uploaded results are stored in a completed queue

### Changed
- uploader no longer changes the system_name and version

## [0.5.0] - 2024-04-29

This is a big change, instead of listening to `map.process` events we now listen for updates from
uncharted that has map_area, polygon_legend_area and line_point_legend_area data. Based on this the
system will trigger download messages.

### Added
- download endpoint to cdr to download cog_area json files from uncharted

### Changed
- new logic on when to trigger download message and for what model.
- server now uses /cdr/ as prefix to the hook/download code

## [0.4.0] - 2024-04-29

### Added
- can now set a prefix for all queue names (PREFIX="")

### Changed
- renamed server folder to cdrhook
- monitor shows number of messages processing, "61 / 1" means 61 messages waiting, 1 being processed
- both uploader and pipeline are now part of profile pipeline

### Fixed
- RabbitMQ is now pinned to v3.13

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
