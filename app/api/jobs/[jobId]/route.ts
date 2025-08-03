import { NextRequest, NextResponse } from 'next/server';
import { getJob } from 'app/db';

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const { jobId } = params;

    if (!jobId) {
      return NextResponse.json(
        { error: 'Job ID is required' },
        { status: 400 }
      );
    }

    const job = await getJob(jobId);

    if (!job) {
      return NextResponse.json(
        { error: 'Job not found' },
        { status: 404 }
      );
    }

    // Return job status and progress
    return NextResponse.json({
      id: job.id,
      status: job.status,
      progress: {
        current: job.progress_current,
        total: job.progress_total
      },
      file_name: job.file_name,
      file_size: job.file_size,
      result: job.result,
      error_message: job.error_message,
      created_at: job.created_at,
      updated_at: job.updated_at
    });

  } catch (error) {
    console.error('Job status fetch error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}