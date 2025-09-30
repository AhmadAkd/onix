import csv
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class ExportService:
    """Service for exporting health check results and server data."""

    @staticmethod
    def export_health_stats_to_csv(servers: List[Dict[str, Any]],
                                   health_stats: Dict[str, Dict],
                                   filename: str = None) -> str:
        """Export health check statistics to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_check_results_{timestamp}.csv"

        filepath = Path(filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Server Name', 'Server ID', 'Protocol', 'Address', 'Port',
                'TCP Ping (ms)', 'URL Ping (ms)', 'TCP EMA (ms)', 'URL EMA (ms)',
                'Failures', 'Last Test', 'Status', 'Export Time'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for server in servers:
                server_id = server.get('id', '')
                stats = health_stats.get(server_id, {})

                # Calculate status
                failures = stats.get('failures', 0)
                if failures == 0:
                    status = 'Online'
                elif failures < 3:
                    status = 'Unstable'
                else:
                    status = 'Offline'

                # Format last test time
                last_test = stats.get('last_test', 0)
                if last_test > 0:
                    last_test_str = datetime.fromtimestamp(
                        last_test).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    last_test_str = 'Never'

                writer.writerow({
                    'Server Name': server.get('name', 'Unknown'),
                    'Server ID': server_id,
                    'Protocol': server.get('protocol', 'Unknown'),
                    'Address': server.get('server', 'Unknown'),
                    'Port': server.get('port', 'Unknown'),
                    'TCP Ping (ms)': server.get('tcp_ping', 'N/A'),
                    'URL Ping (ms)': server.get('url_ping', 'N/A'),
                    'TCP EMA (ms)': f"{stats.get('tcp_ema', 0):.1f}" if stats.get('tcp_ema') else 'N/A',
                    'URL EMA (ms)': f"{stats.get('url_ema', 0):.1f}" if stats.get('url_ema') else 'N/A',
                    'Failures': failures,
                    'Last Test': last_test_str,
                    'Status': status,
                    'Export Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        return str(filepath.absolute())

    @staticmethod
    def export_server_list_to_csv(servers: List[Dict[str, Any]],
                                  filename: str = None) -> str:
        """Export server list to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"server_list_{timestamp}.csv"

        filepath = Path(filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Name', 'Protocol', 'Address', 'Port', 'UUID', 'Password',
                'Encryption', 'Security', 'Network', 'TLS', 'SNI', 'ALPN',
                'TCP Ping (ms)', 'URL Ping (ms)', 'Export Time'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for server in servers:
                writer.writerow({
                    'Name': server.get('name', 'Unknown'),
                    'Protocol': server.get('protocol', 'Unknown'),
                    'Address': server.get('server', 'Unknown'),
                    'Port': server.get('port', 'Unknown'),
                    'UUID': server.get('uuid', 'N/A'),
                    'Password': server.get('password', 'N/A'),
                    'Encryption': server.get('encryption', 'N/A'),
                    'Security': server.get('security', 'N/A'),
                    'Network': server.get('network', 'N/A'),
                    'TLS': server.get('tls', 'N/A'),
                    'SNI': server.get('sni', 'N/A'),
                    'ALPN': server.get('alpn', 'N/A'),
                    'TCP Ping (ms)': server.get('tcp_ping', 'N/A'),
                    'URL Ping (ms)': server.get('url_ping', 'N/A'),
                    'Export Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

        return str(filepath.absolute())
