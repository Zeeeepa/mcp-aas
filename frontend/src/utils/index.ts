export const formatDate = (date: Date): string => {
  return date.toISOString();
};

export const generateUrlPath = (toolId: string): string => {
  return `/api/tools/${toolId}/connect`;
};

