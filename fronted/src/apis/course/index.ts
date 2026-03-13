import { serverApi, type Response } from '@/apis'
import type { CourseList } from '@en/common/course'

export const getCourseList = (): Promise<Response<CourseList>> => {
  return serverApi.get('/course/list')
}
export const getMyCourse = (): Promise<Response<CourseList>> => {
  return serverApi.get('/course/my')
}
