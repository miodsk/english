export type ExamType = "ielts" | "cet-4" | "cet-6" | "kaoyan";
export type TaskType =
    | "data_graph"
    | "image_drawing"
    | "process_map"
    | "opinion_essay"
    | "letter"
    | "notice";

// ====== /ai/composition/grade ======
export interface CompositionGradeRequest {
    essay_text: string;
    exam_type: ExamType;
    task_type: TaskType;
    topic: string;
    user_id: string;
    thread_id?: string | null;
    session_id?: string | null;
}

export interface CompositionGradeResponse {
    thread_id: string;
    scores: Record<string, number>;
    band_score: number;
    score_explanation?: string | null;
    errors: Record<string, any>[];
    suggestions: string[];
    current_step?: string | null;
    needs_revision: boolean;
}

// ====== /ai/composition/revise ======
export interface CompositionReviseRequest {
    revised_essay: string;
    thread_id: string;
    session_id?: string | null;
    user_id?: string | null;
    topic?: string | null;
    exam_type?: ExamType | null;
    task_type?: TaskType | null;
}

export interface CompositionReviseResponse extends CompositionGradeResponse {
    previous_band_score: number;
    delta: number;
    improved: boolean;
}

export interface CompositionHistoryThread {
    thread_id: string;
    session_id?: string | null;
    topic?: string | null;
    exam_type?: ExamType | null;
    task_type?: TaskType | null;
    last_band_score?: number | null;
    updated_at: string;
    preview?: string | null;
}

export interface CompositionHistoryMessage {
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
}

export interface CompositionHistoryListResponse {
    threads: CompositionHistoryThread[];
}

export interface CompositionHistoryDetailResponse {
    thread_id: string;
    session_id?: string | null;
    topic?: string | null;
    exam_type?: ExamType | null;
    task_type?: TaskType | null;
    messages: CompositionHistoryMessage[];
}
