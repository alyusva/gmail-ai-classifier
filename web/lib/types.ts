export interface Email {
  id: string
  thread_id: string | null
  subject: string | null
  sender: string | null
  sender_email: string | null
  snippet: string | null
  date: string | null
  labels_original: string[] | null
  is_read: boolean
  extracted_at: string
}

export interface Classification {
  email_id: string
  labels: string[] | null
  confidence: number
  classified_at: string
  applied: boolean
  applied_at: string | null
}

export interface Taxonomy {
  label: string
  gmail_label_id: string
  created_at: string
}

export interface Progress {
  key: string
  value: string | null
  updated_at: string
}

export interface ClassificationSummary {
  label: string
  email_count: number
}

export interface EmailWithClassification extends Email {
  classifications: Pick<Classification, 'labels' | 'applied' | 'classified_at' | 'confidence'> | null
}
