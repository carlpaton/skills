# Changelog

Changes to the `infra` plugin. Versions follow `version` in `.claude-plugin/plugin.json`.

## 0.1.1

### Fixed

- `tf-pgsql`: pin `zone = "1"` on the PostgreSQL Flexible Server. Leaving it unset let Azure assign a zone, and the provider then failed the apply with `zone can only be changed when exchanged with the zone specified in high_availability.0.standby_availability_zone`. The skill note now explains this.

## 0.1.0

- Initial release: `tf-web`, `tf-worker`, `tf-blob`, `tf-foundry` and `tf-pgsql`.
