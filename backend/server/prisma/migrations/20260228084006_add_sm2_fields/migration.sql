/*
  Warnings:

  - You are about to drop the column `newInterval` on the `ReviewLog` table. All the data in the column will be lost.
  - You are about to drop the column `prevInterval` on the `ReviewLog` table. All the data in the column will be lost.
  - You are about to drop the column `target` on the `User` table. All the data in the column will be lost.
  - You are about to drop the `Essay` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `Example` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "Essay" DROP CONSTRAINT "Essay_userId_fkey";

-- DropForeignKey
ALTER TABLE "Example" DROP CONSTRAINT "Example_wordId_fkey";

-- DropIndex
DROP INDEX "ReviewLog_createdAt_idx";

-- AlterTable
ALTER TABLE "ReviewLog" DROP COLUMN "newInterval",
DROP COLUMN "prevInterval";

-- AlterTable
ALTER TABLE "User" DROP COLUMN "target",
ALTER COLUMN "email" DROP NOT NULL;

-- DropTable
DROP TABLE "Essay";

-- DropTable
DROP TABLE "Example";

-- CreateIndex
CREATE INDEX "ReviewLog_recordId_idx" ON "ReviewLog"("recordId");
