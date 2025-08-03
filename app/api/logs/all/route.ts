import { NextRequest, NextResponse } from 'next/server';
import { CloudWatchLogsClient, FilterLogEventsCommand } from '@aws-sdk/client-cloudwatch-logs';

// Force dynamic rendering - prevent static generation at build time
export const dynamic = 'force-dynamic';
export const revalidate = 0;

// Initialize CloudWatch Logs client
const cloudWatchLogs = new CloudWatchLogsClient({
  region: 'us-west-2',
  credentials: process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY ? {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  } : undefined,
});

const PROCESSING_LOG_GROUP = process.env.PROCESSING_LOG_GROUP || '/aws/lambda/InfraStack-GridParserProcessingLambdaGridParserFun-ZE6Hc3YH3rcO';
const PARSER_LOG_GROUP = process.env.PARSER_LOG_GROUP || '/aws/lambda/InfraStack-GridParserApiLambdaGridParserFunctionFF-E3nRvJfdvN68';

export async function GET(request: NextRequest) {
  // Force dynamic rendering - prevent static generation
  const headers = new Headers();
  headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
  
  // Ensure this route is always dynamic
  const timestamp = Date.now();
  const searchParams = new URL(request.url).searchParams;
  const bustParam = searchParams.get('t') || timestamp;

  try {
    // Get logs from the last 10 minutes
    const startTime = Date.now() - (10 * 60 * 1000);
    
    // Fetch logs from both Lambda functions
    const logGroups = [PROCESSING_LOG_GROUP, PARSER_LOG_GROUP];
    const allLogs: any[] = [];

    for (const logGroupName of logGroups) {
      try {
        const command = new FilterLogEventsCommand({
          logGroupName,
          startTime,
          limit: 500,
        });

        const response = await cloudWatchLogs.send(command);
        
        const groupLogs = response.events?.map(event => ({
          id: `${logGroupName}-${event.eventId}`,
          timestamp: event.timestamp || Date.now(),
          message: event.message || '',
          logGroup: logGroupName.split('/').pop(),
        })) || [];

        allLogs.push(...groupLogs);
      } catch (groupError) {
        console.error(`Failed to fetch logs from ${logGroupName}:`, groupError);
        // Continue with other log groups
      }
    }

    // Sort all logs by timestamp
    allLogs.sort((a, b) => a.timestamp - b.timestamp);

    const response = NextResponse.json({
      logs: allLogs,
      totalEvents: allLogs.length,
      timeWindow: '10 minutes',
      timestamp: Date.now(),
      requestId: bustParam
    });

    // Prevent all forms of caching
    response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0');
    response.headers.set('Pragma', 'no-cache');
    response.headers.set('Expires', '0');
    response.headers.set('Surrogate-Control', 'no-store');
    response.headers.set('X-Accel-Expires', '0');
    
    return response;

  } catch (error) {
    console.error('CloudWatch logs fetch error:', error);
    
    const errorResponse = NextResponse.json(
      { 
        error: 'Failed to fetch logs',
        details: error instanceof Error ? error.message : 'Unknown error',
        logs: []
      },
      { status: 200 }
    );

    // Prevent caching of error responses too
    errorResponse.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
    errorResponse.headers.set('Pragma', 'no-cache');
    errorResponse.headers.set('Expires', '0');
    
    return errorResponse;
  }
}