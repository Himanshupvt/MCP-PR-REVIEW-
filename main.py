import sys
import os
import traceback
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from github_integration import fetch_pr_changes
from notion_client import Client
from dotenv import load_dotenv


class PRAnalyzer:
    def __init__(self):
        print("🟡 Loading environment variables...", file=sys.stderr)
        load_dotenv()

        print("🛠️ Initializing MCP Server...", file=sys.stderr)
        self.mcp = FastMCP("github_pr_analysis")

        print("🔑 Initializing Notion integration...", file=sys.stderr)
        self._init_notion()

        print("🔧 Registering MCP tools...", file=sys.stderr)
        self._register_tools()

    def _init_notion(self):
        self.notion_api_key = os.getenv("NOTION_TOKEN")
        self.notion_page_id = os.getenv("NOTION_DATABASE_ID")

        # Log environment values safely
        print(f"🔐 NOTION_TOKEN Loaded: {'Yes' if self.notion_api_key else 'No'}", file=sys.stderr)
        print(f"📄 NOTION_DATABASE_ID: {self.notion_page_id}", file=sys.stderr)

        if not self.notion_api_key or not self.notion_page_id:
            raise ValueError("❌ Missing Notion credentials in .env")
        self.notion = Client(auth=self.notion_api_key)

    def _register_tools(self):
        @self.mcp.tool()
        async def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
            print(f"📥 MCP tool `fetch_pr` called with: {repo_owner}/{repo_name}#{pr_number}", file=sys.stderr)
            return fetch_pr_changes(repo_owner, repo_name, pr_number) or {}

        @self.mcp.tool()
        async def create_notion_page(title: str, content: str) -> str:
            print(f"📝 Creating Notion page: {title}", file=sys.stderr)
            try:
                self.notion.pages.create(
                    parent={"type": "page_id", "page_id": self.notion_page_id},
                    properties={"title": {"title": [{"text": {"content": title}}]}},
                    children=[{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": content}
                            }]
                        }
                    }]
                )
                print(f"✅ Notion page '{title}' created successfully", file=sys.stderr)
                return f"Notion page '{title}' created!"
            except Exception as e:
                traceback.print_exc()
                return f"❌ Error creating Notion page: {str(e)}"

    def run(self):
        print("🚀 Running MCP server for GitHub PR Analysis...", file=sys.stderr)
        self.mcp.run(transport="stdio")


if __name__ == "__main__":
    print("🔁 Starting PRAnalyzer...", file=sys.stderr)
    try:
        analyzer = PRAnalyzer()
        print("✅ PRAnalyzer initialized", file=sys.stderr)
        analyzer.run()
    except Exception as e:
        print("❌ Error during startup:", file=sys.stderr)
        traceback.print_exc()
