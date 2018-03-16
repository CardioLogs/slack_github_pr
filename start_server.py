import logging
import sys

from slack_github_pr.web import run_server


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
    server_host = sys.argv[1] if len(sys.argv) >= 2 else '0.0.0.0'
    server_port = int(sys.argv[2]) if len(sys.argv) >= 3 else 8008
    run_server(server_host, server_port)
