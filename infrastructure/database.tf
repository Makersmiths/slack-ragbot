resource "random_integer" "ri" {
  min = 10000
  max = 99999
}

resource "azurerm_cosmosdb_account" "db_account" {
  name                = "rag-cosmos-db-${random_integer.ri.result}"
  location            = azurerm_resource_group.rag_rg.location
  resource_group_name = azurerm_resource_group.rag_rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"
  public_network_access_enabled = true
  automatic_failover_enabled = false
  multiple_write_locations_enabled = false
  is_virtual_network_filter_enabled = true
  free_tier_enabled = true
  analytical_storage_enabled = false
  minimal_tls_version = "Tls12"
  ip_range_filter = [azurerm_public_ip.rag_public_ip.ip_address]
  network_acl_bypass_for_azure_services = true

  analytical_storage {
    schema_type = "WellDefined"
  }

  virtual_network_rule {
    id = azurerm_subnet.rag_compute_subnet.id
    ignore_missing_vnet_service_endpoint = false
  }

  capabilities {
    name = "DeleteAllItemsByPartitionKey"
  }

  capabilities {
    name = "EnableNoSQLVectorSearch"
  }

  consistency_policy {
    consistency_level       = "BoundedStaleness"
    max_interval_in_seconds = 300
    max_staleness_prefix    = 100000
  }

  geo_location {
    location          = "eastus2"
    failover_priority = 0
    zone_redundant = false
  }
  virtual_network_rule {
    id = azurerm_subnet.rag_compute_subnet.id
  }

  backup {
    type = "Periodic"
    interval_in_minutes = 1440
    retention_in_hours = 8
    storage_redundancy = "Geo"
  }
  
}

resource "azurerm_cosmosdb_sql_database" "rag_db" {
  name                = "vectorDB"
  resource_group_name = azurerm_resource_group.rag_rg.name
  account_name        = azurerm_cosmosdb_account.db_account.name
  throughput = 400
  depends_on = [ azurerm_cosmosdb_account.db_account ]
}

resource "azurerm_cosmosdb_sql_container" "rag_container" {
  name                  = "vectorContainer"
  resource_group_name = azurerm_resource_group.rag_rg.name
  account_name        = azurerm_cosmosdb_account.db_account.name
  database_name         = azurerm_cosmosdb_sql_database.rag_db.name
  partition_key_paths   = ["/myPartitionKey"]
  partition_key_version = 1
  throughput            = 400
  partition_key_kind = "Hash"
  
  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/embedding/*"
    }
    excluded_path {
      path = "/_etag/?"
    }
  }
}