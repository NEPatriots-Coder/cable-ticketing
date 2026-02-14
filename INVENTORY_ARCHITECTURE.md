# Inventory Architecture Additions

## Goal
Track:
- What was requested/used by subcontractors (tickets).
- What was received into stock (cable receiving).
- Current on-hand quantity by cable SKU.

## Collections

### `tickets`
Existing workflow entity. Consumption is recorded when a ticket first transitions to `fulfilled`.

### `cable_receiving`
Inbound inventory records.

Document shape:
- `id`
- `vendor`
- `po_number`
- `items: [{ cable_type, cable_length, quantity }]`
- `notes`
- `received_by_id`
- `received_at`
- `created_at`

### `inventory_movements`
Immutable ledger of stock deltas.

Document shape:
- `id`
- `movement_type` (`receipt`, `consumption`, `adjustment`)
- `source_type` (`cable_receiving`, `ticket_fulfillment`, ...)
- `source_id`
- `actor_user_id`
- `cable_type`
- `cable_length`
- `quantity_delta` (`+` for incoming, `-` for outgoing)
- `notes`
- `created_at`

## On-Hand Formula

For each SKU (`cable_type`, `cable_length`):

`on_hand = sum(quantity_delta in inventory_movements)`

## Implemented API

- `POST /api/cable-receiving`
  - Admin-only
  - Creates receipt and positive inventory movements
- `GET /api/cable-receiving`
  - Lists receipt history
- `GET /api/inventory/movements`
  - Lists movement ledger
  - Filters: `movement_type`, `source_type`, `source_id`, `limit`
- `GET /api/inventory/on-hand`
  - Returns grouped on-hand by SKU
  - Query: `include_zero=true|false`

## Ticket Integration

When a ticket is marked `fulfilled` for the first time:
- Create one `consumption` movement per item.
- Use `source_type=ticket_fulfillment` and `source_id=ticket.id`.
- Guard against duplicates by checking existing movements for that source.

## BOM Phase (Next)

Add `bom_documents`:
- `project_id`, `version`, `status`
- `items: [{ cable_type, cable_length, qty_planned, tolerance_pct }]`

Then compare:
- `planned (BOM)` vs `issued/used (movements)` vs `requested (tickets)`.
