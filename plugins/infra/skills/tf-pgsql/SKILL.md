---
name: tf-pgsql
description: Add an Azure PostgreSQL Flexible Server to an existing Terraform web or worker environment created by tf-web or tf-worker. The admin password is a required variable with no default. Use when the user wants a database on an existing service.
argument-hint: [sku]
---

# Terraform add-on: PostgreSQL

Adds a PostgreSQL Flexible Server and an Azure-services firewall rule to existing environment directories.

## Inputs

| Input | Notes |
|-------|-------|
| `psql_sku` | Default `B_Standard_B1ms` for uat. Ask for prod, as a burstable SKU is rarely right there. |
| environments | Which directories. |

The admin user defaults to `<prefix>_psql_admin`. The password is never asked for and never written: it is the required variable `psql_admin_pass`, supplied with `TF_VAR_psql_admin_pass` or a git-ignored `terraform.tfvars`.

## Add

1. Find the target directories and read `prefix`, `service` and `env`, as in [../tf-blob/SKILL.md](../tf-blob/SKILL.md) step 1. Stop if there is no base to attach to.
2. Render [pgsql.tf.tmpl](pgsql.tf.tmpl) to `pgsql.tf` and append [vars-extra.tf.tmpl](vars-extra.tf.tmpl) to `vars.tf`.
3. Add `psql_admin_pass` to `{{extra_secret_vars}}` in `docs/state-bootstrap.md` (write it as ` and `TF_VAR_psql_admin_pass``).
4. Run the checks from the base doc.
5. Report that the firewall rule `0.0.0.0` allows every Azure service, including other customers' subscriptions, and should be tightened before production holds real data. Database scripts belong in `sql/`, kept apart from Terraform, and are not created here.

## Notes

- Changing the SKU or version later can force a replace. Read the plan for any destroy.
- `zone` is pinned to `"1"`. If it is unset, Azure assigns a zone at creation and the provider then fails the apply with `zone can only be changed when exchanged with the zone specified in high_availability.0.standby_availability_zone`. Zone 1 exists in every region that supports zones. For a region without zone support, remove the line.
