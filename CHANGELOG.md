# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
