export type ChatRole = 'human' | 'ai'
export type ChatRoleType = 'kobe' | 'sakiko'
export type ChatMessage = {
    role: ChatRole;
    content: string;
}
export type ChatMessageList = ChatMessage[]

export type ChatMode = {
    label: string;
    id: string
    role: ChatRole
}
export type ChatModeList = ChatMode[]
export type ChatDto = {
    role: ChatRoleType;
    content: string;
    userId: string
}
// 线程ID userId-role

