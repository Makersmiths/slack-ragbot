
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
  computer_name = "rag-compute"
  resource_group_name = azurerm_resource_group.rag_rg.name
  location            = azurerm_resource_group.rag_rg.location
  size                = "Standard_B1s"
  admin_username      = "adminuser"

  network_interface_ids = [
    azurerm_network_interface.rag_compute_nic.id,
  ]
  zone = 1
  
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
  role_definition_name = "Azure AI Developer"
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