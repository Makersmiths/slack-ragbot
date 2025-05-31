
resource "azurerm_network_interface" "rag_compute_nic" {
  name                = "rag_nic"
  location            = azurerm_resource_group.rag_rg.location
  resource_group_name = azurerm_resource_group.rag_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.rag_compute_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id = azurerm_public_ip.rag_public_ip.id
  }
}

resource "azurerm_linux_virtual_machine" "rag_compute" {
  name                = "rag_compute"
  computer_name       = "rag-compute"
  resource_group_name = azurerm_resource_group.rag_rg.name
  location            = azurerm_resource_group.rag_rg.location
  size                = "Standard_B1s"
  admin_username      = "adminuser"

  network_interface_ids = [
    azurerm_network_interface.rag_compute_nic.id,
  ]
  zone = 1
  custom_data = base64encode("setup.sh")
  
  secure_boot_enabled = true
  vtpm_enabled = true
  admin_ssh_key {
    username   = "adminuser"
    public_key = azurerm_ssh_public_key.rag_pub_key.public_key
  }
    
  identity {
    type = "SystemAssigned"
  }

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }
  
  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }
  disk_controller_type = "SCSI"
  

  source_image_reference {
    publisher = "Canonical"
    offer     = "ubuntu-24_04-lts"
    sku       = "server"
    version   = "latest"
  }
}

resource "azurerm_role_assignment" "compute-ai-dev-role" {
  scope                = data.azurerm_subscription.primary.id
  role_definition_name = "Cognitive Services Contributor"
  principal_id         = azurerm_linux_virtual_machine.rag_compute.identity[0].principal_id
}

resource "azurerm_role_assignment" "compute-reader-role" {
  scope                = data.azurerm_subscription.primary.id
  role_definition_name = "Reader"
  principal_id         = azurerm_linux_virtual_machine.rag_compute.identity[0].principal_id
}

resource "azurerm_role_assignment" "compute-cosmos-reader-role" {
  scope                = data.azurerm_subscription.primary.id
  role_definition_name = "Cosmos DB Account Reader Role"
  principal_id         = azurerm_linux_virtual_machine.rag_compute.identity[0].principal_id
}

resource "azurerm_role_assignment" "compute-keyvault-secret-user" {
  scope                = data.azurerm_subscription.primary.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = azurerm_linux_virtual_machine.rag_compute.identity[0].principal_id
}

resource "azurerm_cosmosdb_sql_role_assignment" "cosmosdb_role_assignment" {
  account_name      = azurerm_cosmosdb_account.db_account.name
  resource_group_name = azurerm_resource_group.rag_rg.name
  scope             = azurerm_cosmosdb_account.db_account.id
  principal_id      = azurerm_linux_virtual_machine.rag_compute.identity[0].principal_id
  role_definition_id = azurerm_cosmosdb_sql_role_definition.cosmos-metadata-role-def.id
  depends_on = [ azurerm_cosmosdb_sql_role_definition.cosmos-metadata-role-def]
}

resource "azurerm_cosmosdb_sql_role_definition" "cosmos-metadata-role-def" {
  role_definition_id = "00000000-1928-0000-0000-000000000002"
  resource_group_name = azurerm_resource_group.rag_rg.name
  account_name        = azurerm_cosmosdb_account.db_account.name
  name                = "cosmos-metadata-read-roleacctestsqlrole"
  assignable_scopes = [
    azurerm_cosmosdb_account.db_account.id
  ]

  permissions {
    data_actions = ["Microsoft.DocumentDB/databaseAccounts/readMetadata", "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/delete"]
  }
}