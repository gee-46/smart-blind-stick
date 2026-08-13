import { api } from "./api";
import { Contact, ContactInput } from "../types/api";

export async function listContacts(): Promise<Contact[]> {
  const response = await api.get<Contact[]>("/api/contacts");
  return response.data;
}

export async function addContact(input: ContactInput): Promise<Contact> {
  const response = await api.post<Contact>("/api/contacts", input);
  return response.data;
}

export async function updateContact(id: number, input: ContactInput): Promise<Contact> {
  const response = await api.put<Contact>(`/api/contacts/${id}`, input);
  return response.data;
}

export async function deleteContact(id: number): Promise<void> {
  await api.delete(`/api/contacts/${id}`);
}
