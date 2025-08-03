import { drizzle } from 'drizzle-orm/postgres-js';
import { pgTable, serial, varchar, text, jsonb, timestamp, integer } from 'drizzle-orm/pg-core';
import { eq } from 'drizzle-orm';
import postgres from 'postgres';
import { genSaltSync, hashSync } from 'bcrypt-ts';

// Optionally, if not using email/pass login, you can
// use the Drizzle adapter for Auth.js / NextAuth
// https://authjs.dev/reference/adapter/drizzle
let client = postgres(process.env.DATABASE_URL!);
let db = drizzle(client);

export async function getUser(email: string) {
  const users = await ensureTableExists();
  return await db.select().from(users).where(eq(users.email, email));
}

export async function createUser(email: string, password: string) {
  const users = await ensureTableExists();
  let salt = genSaltSync(10);
  let hash = hashSync(password, salt);

  return await db.insert(users).values({ email, password: hash });
}

async function ensureTableExists() {
  const result = await client`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND table_name = 'User'
    );`;

  if (!result[0].exists) {
    await client`
      CREATE TABLE "User" (
        id SERIAL PRIMARY KEY,
        email VARCHAR(64),
        password VARCHAR(64)
      );`;
  }

  const table = pgTable('User', {
    id: serial('id').primaryKey(),
    email: varchar('email', { length: 64 }),
    password: varchar('password', { length: 64 }),
  });

  return table;
}

async function ensureParseAuditsTableExists() {
  const result = await client`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND table_name = 'parse_audits'
    );`;

  if (!result[0].exists) {
    await client`
      CREATE TABLE "parse_audits" (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        file_name TEXT,
        parsed_json JSONB,
        vector_id TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT
      );`;
  }

  const table = pgTable('parse_audits', {
    id: serial('id').primaryKey(),
    user_id: text('user_id'),
    file_name: text('file_name'),
    parsed_json: jsonb('parsed_json'),
    vector_id: text('vector_id'),
    timestamp: timestamp('timestamp').defaultNow(),
    status: text('status'),
  });

  return table;
}

export async function createParseAudit(
  userId: string,
  fileName: string,
  parsedJson: any,
  vectorId: string,
  status: string
) {
  const parseAudits = await ensureParseAuditsTableExists();
  return await db.insert(parseAudits).values({
    user_id: userId,
    file_name: fileName,
    parsed_json: parsedJson,
    vector_id: vectorId,
    status: status,
  });
}

export async function getParseAudits(userId: string) {
  const parseAudits = await ensureParseAuditsTableExists();
  return await db.select().from(parseAudits).where(eq(parseAudits.user_id, userId));
}

// Job processing table for async operations
async function ensureJobsTableExists() {
  const result = await client`
    SELECT EXISTS (
      SELECT FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND table_name = 'processing_jobs'
    );`;

  if (!result[0].exists) {
    await client`
      CREATE TABLE "processing_jobs" (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        file_name TEXT,
        file_size INTEGER,
        status TEXT DEFAULT 'pending',
        progress_current INTEGER DEFAULT 0,
        progress_total INTEGER DEFAULT 0,
        result JSONB,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );`;
  }

  const table = pgTable('processing_jobs', {
    id: text('id').primaryKey(),
    user_id: text('user_id'),
    file_name: text('file_name'),
    file_size: integer('file_size'),
    status: text('status').default('pending'),
    progress_current: integer('progress_current').default(0),
    progress_total: integer('progress_total').default(0),
    result: jsonb('result'),
    error_message: text('error_message'),
    created_at: timestamp('created_at').defaultNow(),
    updated_at: timestamp('updated_at').defaultNow(),
  });

  return table;
}

export async function createJob(
  jobId: string,
  userId: string,
  fileName: string,
  fileSize: number,
  totalChunks: number
) {
  const jobs = await ensureJobsTableExists();
  return await db.insert(jobs).values({
    id: jobId,
    user_id: userId,
    file_name: fileName,
    file_size: fileSize,
    status: 'pending',
    progress_current: 0,
    progress_total: totalChunks,
  });
}

export async function updateJobProgress(
  jobId: string,
  currentChunk: number,
  status: string = 'processing'
) {
  const jobs = await ensureJobsTableExists();
  return await db.update(jobs)
    .set({ 
      progress_current: currentChunk,
      status: status,
      updated_at: new Date()
    })
    .where(eq(jobs.id, jobId));
}

export async function completeJob(
  jobId: string,
  result: any,
  status: string = 'completed'
) {
  const jobs = await ensureJobsTableExists();
  return await db.update(jobs)
    .set({ 
      status: status,
      result: result,
      updated_at: new Date()
    })
    .where(eq(jobs.id, jobId));
}

export async function failJob(
  jobId: string,
  errorMessage: string
) {
  const jobs = await ensureJobsTableExists();
  return await db.update(jobs)
    .set({ 
      status: 'failed',
      error_message: errorMessage,
      updated_at: new Date()
    })
    .where(eq(jobs.id, jobId));
}

export async function getJob(jobId: string) {
  const jobs = await ensureJobsTableExists();
  const result = await db.select().from(jobs).where(eq(jobs.id, jobId));
  return result[0] || null;
}


