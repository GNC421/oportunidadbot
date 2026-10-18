export type Alert = {
  id: number;
  title: string;
  content: string;
  url: string | null;
  author: string;
  detected_at: string | null;
  sent_at: string | null;
  source_url: string | null;
};
