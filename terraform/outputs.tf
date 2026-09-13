output "node_public_ip" {
  description = "Public IP of the k3s node"
  value       = aws_instance.k3s_node.public_ip
}

output "ssh_command" {
  description = "Quick SSH command to reach the node"
  value       = "ssh ubuntu@${aws_instance.k3s_node.public_ip}"
}

output "kubeconfig_fetch_command" {
  description = "Command to pull the kubeconfig down locally"
  value       = "scp ubuntu@${aws_instance.k3s_node.public_ip}:/etc/rancher/k3s/k3s.yaml ./kubeconfig.yaml && sed -i '' 's/127.0.0.1/${aws_instance.k3s_node.public_ip}/' ./kubeconfig.yaml"
}
