resource "azurerm_public_ip" "rag_public_ip" {
  name                = "rag_public_ip"
  resource_group_name = azurerm_resource_group.rag_rg.name
  location            = azurerm_resource_group.rag_rg.location
  allocation_method   = "Static"
  sku_tier = "Regional"
  zones= ["1"]
  ip_version = "IPv4"
  idle_timeout_in_minutes = 4

  tags = {
    environment = "Production"
  }
}

resource "azurerm_virtual_network" "rag_virtual_network" {
  name                = "rag-network"
  location            = azurerm_resource_group.rag_rg.location
  resource_group_name = azurerm_resource_group.rag_rg.name
  address_space       = ["10.0.0.0/24"]
  private_endpoint_vnet_policies = "Disabled"

  encryption {
    enforcement = "AllowUnencrypted"

  }
  tags = {
    environment = "Production"
  }
}


resource "azurerm_subnet" "rag_compute_subnet" {
  name                 = "compute"
  resource_group_name  = azurerm_resource_group.rag_rg.name
  virtual_network_name = azurerm_virtual_network.rag_virtual_network.name
  address_prefixes     = ["10.0.0.0/28"]
  service_endpoints = ["Microsoft.AzureCosmosDB", "Microsoft.KeyVault", "Microsoft.CognitiveServices"]
  private_endpoint_network_policies = "Disabled"
  private_link_service_network_policies_enabled = true

}

resource "azurerm_network_security_group" "rag_nsg" {
  name                = "rag-nsg"
  location            = azurerm_resource_group.rag_rg.location
  resource_group_name = azurerm_resource_group.rag_rg.name

  security_rule {
    name                       = "SSH"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.management_ip
    destination_address_prefix = "*"
  }

  tags = {
    environment = "Production"
  }
}

resource "azurerm_subnet_network_security_group_association" "compute_nsg_associationexample" {
  subnet_id                 = azurerm_subnet.rag_compute_subnet.id
  network_security_group_id = azurerm_network_security_group.rag_nsg.id
}