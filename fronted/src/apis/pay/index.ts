import { serverApi, type Response } from '@/apis'
import type { CreatePayDto, ResultPay } from '@en/common/pay/index'

export const createPay = (data: CreatePayDto): Promise<Response<ResultPay>> => {
  return serverApi.post('/pay/create', data)
}
