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

# resource "azurerm_key_vault_secret" "slack_app_token" {
#   name         = "slack-app-token"
#   value        = var.slack_app_token
#   key_vault_id = azurerm_key_vault.rag_kv.id
#   depends_on = [ azurerm_key_vault.rag_kv ]
# }
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