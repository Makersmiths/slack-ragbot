provider "azurerm" {
  # Configuration options
    features {
      key_vault {
        purge_soft_delete_on_destroy =  true
      }
      cognitive_account {
        purge_soft_delete_on_destroy = true
      }
      machine_learning {
        purge_soft_deleted_workspace_on_destroy = true
      }
      virtual_machine {
        delete_os_disk_on_deletion = true
      }
    }
    subscription_id = var.subscription_id
}

data "azurerm_client_config" "current" {}

variable "management_ip" {}
variable "rg_name" {}
variable "subscription_id" {}
variable "subdomain_name" {}
variable "confluence_space_key" {}
variable "confluence_url" {}
variable "confluence_token" {}
variable "slack_bot_token" {}
variable "slack_client_secret" {}
variable "slack_client_id" {}
variable "pub_ssh_key_location" {}

resource "azurerm_resource_group" "rag_rg" {
  name     = var.rg_name
  location = "East US 2"
}

resource "azurerm_ssh_public_key" "rag_pub_key" {
  name                = "rag_ssh_key"
  resource_group_name = var.rg_name
  location            = "East US 2"
  public_key          = file(var.pub_ssh_key_location)
    depends_on = [azurerm_resource_group.rag_rg]
}

resource "azurerm_cognitive_account" "rag_cognitive_account" {
  name                = "rag-cognitive-account"
  location            = azurerm_resource_group.rag_rg.location
  resource_group_name = azurerm_resource_group.rag_rg.name
  kind                = "OpenAI"

  sku_name = "S0"
  identity {
    type = "SystemAssigned"
  }
  public_network_access_enabled = true
  local_auth_enabled = true
  custom_subdomain_name = var.subdomain_name
  network_acls {
    bypass = "AzureServices"
    default_action = "Deny"
    ip_rules = []
    virtual_network_rules {
      ignore_missing_vnet_service_endpoint = false
      subnet_id = azurerm_subnet.rag_compute_subnet.id
    }
  }
}

resource "azurerm_cognitive_deployment" "gpt4" {
  name                 = "gpt-4"
  cognitive_account_id = azurerm_cognitive_account.rag_cognitive_account.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  sku {
    name = "Standard"
    capacity = 4
  }
  version_upgrade_option = "OnceNewDefaultVersionAvailable"
}

resource "azurerm_cognitive_deployment" "text_embedding" {
  name                 = "text_embedding"
  cognitive_account_id = azurerm_cognitive_account.rag_cognitive_account.id

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }

  sku {
    name = "Standard"
    capacity = 60
  }
  version_upgrade_option = "OnceNewDefaultVersionAvailable"
}

resource "azurerm_key_vault" "rag_kv" {
  name                        = "slack-rag-kv617241"
  location                    = azurerm_resource_group.rag_rg.location
  resource_group_name         = azurerm_resource_group.rag_rg.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  public_network_access_enabled = true

  sku_name = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get","List", "Set", "Purge", "List", "Delete"
    ]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_linux_virtual_machine.rag_compute.identity[0].principal_id

    secret_permissions = [
      "Get","List", "Set", "Purge", "List", "Delete"
    ]
  }
  network_acls {
    bypass = "AzureServices"
    default_action = "Deny"
    ip_rules = var.management_ip
    virtual_network_subnet_ids = [azurerm_subnet.rag_compute_subnet.id]
  }
}
resource "azurerm_key_vault_secret" "confluence_token" {
  name         = "confluence-token"
  value        = var.confluence_space_key
  key_vault_id = azurerm_key_vault.rag_kv.id
  depends_on = [ azurerm_key_vault.rag_kv ]
}
resource "azurerm_key_vault_secret" "confluence_space_key" {
  name         = "confluence-space-key"
  value        = var.confluence_space_key
  key_vault_id = azurerm_key_vault.rag_kv.id
  depends_on = [ azurerm_key_vault.rag_kv ]
}
resource "azurerm_key_vault_secret" "confluence_url" {
  name         = "confluence-url"
  value        = var.confluence_url
  key_vault_id = azurerm_key_vault.rag_kv.id
  depends_on = [ azurerm_key_vault.rag_kv ]
}
resource "azurerm_key_vault_secret" "slack_client_secret" {
  name         = "slack-app-token"
  value        = var.slack_client_secret
  key_vault_id = azurerm_key_vault.rag_kv.id
  depends_on = [ azurerm_key_vault.rag_kv ]
}
resource "azurerm_key_vault_secret" "slack_bot_token" {
  name         = "slack-bot-token"
  value        = var.slack_bot_token
  key_vault_id = azurerm_key_vault.rag_kv.id
  depends_on = [ azurerm_key_vault.rag_kv ]
}
resource "azurerm_key_vault_secret" "slack_client_id" {
  name         = "slack-client"
  value        = var.slack_client_id
  key_vault_id = azurerm_key_vault.rag_kv.id
  depends_on = [ azurerm_key_vault.rag_kv ]
}