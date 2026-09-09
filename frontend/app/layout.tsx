import type { Metadata } from 'next';
import './globals.css';

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: 'MCPBridge — Enterprise Agent Integration Gateway',
  description: 'Governed MCP server/client integration with permissions, human approval, LangGraph orchestration and tamper-evident auditability.',
  keywords: ['MCP','Model Context Protocol','LangGraph','AI Agents','FastAPI','Enterprise AI','Tool Calling','Human in the Loop','Agent Integration'],
  creator: 'Samadrita Acharya',
  authors: [{name:'Samadrita Acharya',url:'https://github.com/Samadritaacharya'}],
  openGraph: {
    title: 'MCPBridge — Enterprise Agent Integration Gateway',
    description: 'Give AI agents tools. Keep humans in control.',
    type: 'website',
    url: '/',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MCPBridge — Enterprise Agent Integration Gateway',
    description: 'Governed MCP tools, resources, prompts and human-approved enterprise automation.',
  },
};

export default function RootLayout({children}:{children:React.ReactNode}){
  return <html lang="en"><body>{children}</body></html>;
}
