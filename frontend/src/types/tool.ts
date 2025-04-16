// Tool types and interfaces

export interface Tool {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  version: string;
  status: ToolStatus;
  capabilities: ToolCapability[];
  config?: Record<string, any>;
  metadata?: Record<string, any>;
}

export type ToolCategory = 
  | 'developer'
  | 'communication' 
  | 'analytics'
  | 'search'
  | 'code_analysis'
  | 'testing'
  | 'deployment';

export type ToolStatus = 
  | 'active'
  | 'inactive'
  | 'error'
  | 'configuring';

export type ToolCapability =
  | 'code_search'
  | 'semantic_analysis'
  | 'dependency_mapping'
  | 'test_generation'
  | 'performance_analysis'
  | 'security_scanning'
  | 'documentation'
  | 'refactoring';

export interface ToolConfig {
  id: string;
  toolId: string;
  settings: Record<string, any>;
  enabled: boolean;
  lastUpdated: Date;
}

export interface ToolLaunchOptions {
  toolId: string;
  config?: Record<string, any>;
  context?: Record<string, any>;
}
