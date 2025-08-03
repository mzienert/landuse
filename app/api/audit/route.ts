import { NextRequest, NextResponse } from 'next/server';
import { createParseAudit } from '../../db';

export async function POST(request: NextRequest) {
  try {
    const { userId, fileName, parsedJson, vectorId, status } = await request.json();

    if (!userId || !fileName || !status) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    await createParseAudit(userId, fileName, parsedJson, vectorId, status);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to create audit record:', error);
    return NextResponse.json(
      { error: 'Failed to create audit record' },
      { status: 500 }
    );
  }
}