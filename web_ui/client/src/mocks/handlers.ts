import { http, HttpResponse } from 'msw'

export const handlers = [
  // Mock for starting a new scan
  http.post('/api/scans', async () => {
    // Simulate a network delay
    await new Promise(res => setTimeout(res, 200))

    // Simulate a successful response
    return HttpResponse.json(
      {
        scan_id: `scan_${new Date().toISOString()}`,
      },
      {
        status: 202, // Accepted
      }
    )
  }),

  // You can add other handlers here as you build out the UI
  // For example, a handler for GET /api/scans/:scan_id
]
