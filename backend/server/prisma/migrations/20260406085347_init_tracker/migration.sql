-- CreateTable
CREATE TABLE "checkpoint_blobs" (
    "thread_id" TEXT NOT NULL,
    "checkpoint_ns" TEXT NOT NULL DEFAULT '',
    "channel" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "blob" BYTEA,

    CONSTRAINT "checkpoint_blobs_pkey" PRIMARY KEY ("thread_id","checkpoint_ns","channel","version")
);

-- CreateTable
CREATE TABLE "checkpoint_migrations" (
    "v" INTEGER NOT NULL,

    CONSTRAINT "checkpoint_migrations_pkey" PRIMARY KEY ("v")
);

-- CreateTable
CREATE TABLE "checkpoint_writes" (
    "thread_id" TEXT NOT NULL,
    "checkpoint_ns" TEXT NOT NULL DEFAULT '',
    "checkpoint_id" TEXT NOT NULL,
    "task_id" TEXT NOT NULL,
    "idx" INTEGER NOT NULL,
    "channel" TEXT NOT NULL,
    "type" TEXT,
    "blob" BYTEA NOT NULL,
    "task_path" TEXT NOT NULL DEFAULT '',

    CONSTRAINT "checkpoint_writes_pkey" PRIMARY KEY ("thread_id","checkpoint_ns","checkpoint_id","task_id","idx")
);

-- CreateTable
CREATE TABLE "checkpoints" (
    "thread_id" TEXT NOT NULL,
    "checkpoint_ns" TEXT NOT NULL DEFAULT '',
    "checkpoint_id" TEXT NOT NULL,
    "parent_checkpoint_id" TEXT,
    "type" TEXT,
    "checkpoint" JSONB NOT NULL,
    "metadata" JSONB NOT NULL DEFAULT '{}',

    CONSTRAINT "checkpoints_pkey" PRIMARY KEY ("thread_id","checkpoint_ns","checkpoint_id")
);

-- CreateTable
CREATE TABLE "composition_history_messages" (
    "id" BIGSERIAL NOT NULL,
    "user_id" TEXT NOT NULL,
    "thread_id" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "composition_history_messages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "composition_history_threads" (
    "user_id" TEXT NOT NULL,
    "thread_id" TEXT NOT NULL,
    "session_id" TEXT,
    "topic" TEXT,
    "exam_type" TEXT,
    "task_type" TEXT,
    "last_band_score" DOUBLE PRECISION,
    "preview" TEXT,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "composition_history_threads_pkey" PRIMARY KEY ("user_id","thread_id")
);

-- CreateTable
CREATE TABLE "normal_history_messages" (
    "id" BIGSERIAL NOT NULL,
    "user_id" TEXT NOT NULL,
    "thread_id" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "normal_history_messages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "normal_history_threads" (
    "user_id" TEXT NOT NULL,
    "thread_id" TEXT NOT NULL,
    "session_id" TEXT,
    "mode" TEXT,
    "preview" TEXT,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "normal_history_threads_pkey" PRIMARY KEY ("user_id","thread_id")
);

-- CreateTable
CREATE TABLE "speak_history_messages" (
    "id" BIGSERIAL NOT NULL,
    "user_id" TEXT NOT NULL,
    "thread_id" TEXT NOT NULL,
    "role" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "speak_history_messages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "speak_history_threads" (
    "user_id" TEXT NOT NULL,
    "thread_id" TEXT NOT NULL,
    "session_id" TEXT,
    "topic" TEXT,
    "preview" TEXT,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "speak_history_threads_pkey" PRIMARY KEY ("user_id","thread_id")
);

-- CreateTable
CREATE TABLE "Visitor" (
    "id" TEXT NOT NULL,
    "anonymousId" TEXT NOT NULL,
    "userId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "browser" TEXT,
    "os" TEXT,
    "device" TEXT,

    CONSTRAINT "Visitor_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PageView" (
    "id" TEXT NOT NULL,
    "visitorId" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "referrer" TEXT,
    "path" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "PageView_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TrackEvent" (
    "id" TEXT NOT NULL,
    "visitorId" TEXT NOT NULL,
    "event" TEXT NOT NULL,
    "payload" JSONB,
    "url" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "TrackEvent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PerformanceEntry" (
    "id" TEXT NOT NULL,
    "visitorId" TEXT NOT NULL,
    "fp" DOUBLE PRECISION,
    "fcp" DOUBLE PRECISION,
    "lcp" DOUBLE PRECISION,
    "inp" DOUBLE PRECISION,
    "cls" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "PerformanceEntry_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ErrorEntry" (
    "id" TEXT NOT NULL,
    "visitorId" TEXT NOT NULL,
    "error" TEXT NOT NULL,
    "message" TEXT,
    "stack" TEXT,
    "url" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ErrorEntry_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "checkpoint_blobs_thread_id_idx" ON "checkpoint_blobs"("thread_id");

-- CreateIndex
CREATE INDEX "checkpoint_writes_thread_id_idx" ON "checkpoint_writes"("thread_id");

-- CreateIndex
CREATE INDEX "checkpoints_thread_id_idx" ON "checkpoints"("thread_id");

-- CreateIndex
CREATE INDEX "idx_composition_history_messages_thread" ON "composition_history_messages"("user_id", "thread_id", "created_at");

-- CreateIndex
CREATE INDEX "idx_composition_history_threads_updated" ON "composition_history_threads"("user_id", "updated_at" DESC);

-- CreateIndex
CREATE INDEX "idx_normal_history_messages_thread" ON "normal_history_messages"("user_id", "thread_id", "created_at");

-- CreateIndex
CREATE INDEX "idx_normal_history_threads_updated" ON "normal_history_threads"("user_id", "updated_at" DESC);

-- CreateIndex
CREATE INDEX "idx_speak_history_messages_thread" ON "speak_history_messages"("user_id", "thread_id", "created_at");

-- CreateIndex
CREATE INDEX "idx_speak_history_threads_updated" ON "speak_history_threads"("user_id", "updated_at" DESC);

-- CreateIndex
CREATE UNIQUE INDEX "Visitor_anonymousId_key" ON "Visitor"("anonymousId");

-- CreateIndex
CREATE INDEX "Visitor_userId_idx" ON "Visitor"("userId");

-- CreateIndex
CREATE INDEX "Visitor_anonymousId_idx" ON "Visitor"("anonymousId");

-- CreateIndex
CREATE INDEX "PageView_visitorId_createdAt_idx" ON "PageView"("visitorId", "createdAt");

-- CreateIndex
CREATE INDEX "PageView_path_createdAt_idx" ON "PageView"("path", "createdAt");

-- CreateIndex
CREATE INDEX "TrackEvent_visitorId_createdAt_idx" ON "TrackEvent"("visitorId", "createdAt");

-- CreateIndex
CREATE INDEX "TrackEvent_event_createdAt_idx" ON "TrackEvent"("event", "createdAt");

-- CreateIndex
CREATE INDEX "PerformanceEntry_fp_createdAt_idx" ON "PerformanceEntry"("fp", "createdAt");

-- CreateIndex
CREATE INDEX "PerformanceEntry_fcp_createdAt_idx" ON "PerformanceEntry"("fcp", "createdAt");

-- CreateIndex
CREATE INDEX "PerformanceEntry_lcp_createdAt_idx" ON "PerformanceEntry"("lcp", "createdAt");

-- CreateIndex
CREATE INDEX "PerformanceEntry_inp_createdAt_idx" ON "PerformanceEntry"("inp", "createdAt");

-- CreateIndex
CREATE INDEX "PerformanceEntry_cls_createdAt_idx" ON "PerformanceEntry"("cls", "createdAt");

-- CreateIndex
CREATE INDEX "PerformanceEntry_fp_fcp_lcp_inp_cls_createdAt_idx" ON "PerformanceEntry"("fp", "fcp", "lcp", "inp", "cls", "createdAt");

-- CreateIndex
CREATE INDEX "ErrorEntry_visitorId_createdAt_idx" ON "ErrorEntry"("visitorId", "createdAt");

-- CreateIndex
CREATE INDEX "ErrorEntry_error_createdAt_idx" ON "ErrorEntry"("error", "createdAt");

-- AddForeignKey
ALTER TABLE "composition_history_messages" ADD CONSTRAINT "fk_composition_history_thread" FOREIGN KEY ("user_id", "thread_id") REFERENCES "composition_history_threads"("user_id", "thread_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "normal_history_messages" ADD CONSTRAINT "fk_normal_history_thread" FOREIGN KEY ("user_id", "thread_id") REFERENCES "normal_history_threads"("user_id", "thread_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "speak_history_messages" ADD CONSTRAINT "fk_speak_history_thread" FOREIGN KEY ("user_id", "thread_id") REFERENCES "speak_history_threads"("user_id", "thread_id") ON DELETE CASCADE ON UPDATE NO ACTION;

-- AddForeignKey
ALTER TABLE "Visitor" ADD CONSTRAINT "Visitor_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PageView" ADD CONSTRAINT "PageView_visitorId_fkey" FOREIGN KEY ("visitorId") REFERENCES "Visitor"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TrackEvent" ADD CONSTRAINT "TrackEvent_visitorId_fkey" FOREIGN KEY ("visitorId") REFERENCES "Visitor"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PerformanceEntry" ADD CONSTRAINT "PerformanceEntry_visitorId_fkey" FOREIGN KEY ("visitorId") REFERENCES "Visitor"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ErrorEntry" ADD CONSTRAINT "ErrorEntry_visitorId_fkey" FOREIGN KEY ("visitorId") REFERENCES "Visitor"("id") ON DELETE CASCADE ON UPDATE CASCADE;
