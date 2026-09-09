export type InventoryCategory =
  | "CONSUMABLES"
  | "INSTRUMENTS"
  | "EQUIPMENT"
  | "IMPLANTS"
  | "ORTHODONTIC"
  | "ENDODONTIC"
  | "PROSTHODONTIC"
  | "PERIODONTIC"
  | "SURGICAL"
  | "MEDICINES"
  | "LABORATORY"
  | "OFFICE_SUPPLIES";

export type InventoryStatus =
  | "IN_STOCK"
  | "LOW_STOCK"
  | "OUT_OF_STOCK"
  | "DISCONTINUED";

export type BatchStatus = "ACTIVE" | "DEPLETED" | "EXPIRED" | "QUARANTINED";

export type PurchaseOrderStatus =
  | "DRAFT"
  | "SENT"
  | "PARTIALLY_RECEIVED"
  | "RECEIVED"
  | "CANCELLED";

export type StockTransactionType =
  | "PURCHASE_RECEIPT"
  | "TREATMENT_CONSUMPTION"
  | "ADJUSTMENT"
  | "EXPIRY_DISPOSAL"
  | "RETURN_TO_SUPPLIER"
  | "INITIAL_STOCK"
  | "TRANSFER";

export interface Supplier {
  id: string;
  clinic_id: string;
  name: string;
  contact_person?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  tax_id?: string | null;
  payment_terms?: string | null;
  notes?: string | null;
  rating?: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreate {
  name: string;
  contact_person?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  tax_id?: string | null;
  payment_terms?: string | null;
  notes?: string | null;
  rating?: number | null;
}

export interface SupplierUpdate {
  name?: string;
  contact_person?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  tax_id?: string | null;
  payment_terms?: string | null;
  notes?: string | null;
  rating?: number | null;
  is_active?: boolean;
}

export interface InventoryBatch {
  id: string;
  clinic_id: string;
  item_id: string;
  batch_number: string;
  expiry_date?: string | null;
  quantity: number;
  initial_quantity: number;
  purchase_price: number;
  received_date?: string | null;
  po_id?: string | null;
  status: BatchStatus;
  created_at: string;
  updated_at: string;
}

export interface InventoryItem {
  id: string;
  clinic_id: string;
  sku: string;
  name: string;
  generic_name?: string | null;
  category: InventoryCategory;
  supplier_id?: string | null;
  unit: string;
  minimum_stock: number;
  reorder_level: number;
  purchase_price: number;
  selling_price?: number | null;
  tax_rate: number;
  storage_location?: string | null;
  notes?: string | null;
  is_active: boolean;
  current_quantity: number;
  status: InventoryStatus;
  supplier?: Supplier | null;
  created_at: string;
  updated_at: string;
}

export interface StockTransaction {
  id: string;
  clinic_id: string;
  item_id: string;
  item_name?: string | null;
  item_sku?: string | null;
  batch_id?: string | null;
  batch_number?: string | null;
  transaction_type: StockTransactionType;
  quantity: number;
  previous_quantity: number;
  new_quantity: number;
  unit_cost: number;
  total_cost: number;
  reason?: string | null;
  related_treatment_id?: string | null;
  related_invoice_id?: string | null;
  related_po_id?: string | null;
  actor_id?: string | null;
  actor_name?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface InventoryItemDetail extends InventoryItem {
  batches: InventoryBatch[];
  recent_transactions: StockTransaction[];
}

export interface InventoryItemCreate {
  name: string;
  generic_name?: string | null;
  category: InventoryCategory;
  supplier_id?: string | null;
  unit: string;
  minimum_stock?: number;
  reorder_level?: number;
  purchase_price: number;
  selling_price?: number | null;
  tax_rate?: number;
  storage_location?: string | null;
  notes?: string | null;
  initial_quantity?: number;
  initial_batch_number?: string | null;
  initial_expiry_date?: string | null;
}

export interface StockAdjustmentCreate {
  adjustment_type: StockTransactionType;
  quantity: number;
  batch_id?: string | null;
  reason: string;
  notes?: string | null;
}

export interface PurchaseOrderItem {
  id: string;
  po_id: string;
  item_id: string;
  item_sku?: string | null;
  item_name?: string | null;
  item_unit?: string | null;
  quantity_ordered: number;
  quantity_received: number;
  unit_price: number;
  tax_rate: number;
  tax_amount: number;
  discount_percent: number;
  discount_amount: number;
  line_total: number;
}

export interface PurchaseOrder {
  id: string;
  clinic_id: string;
  po_number: string;
  supplier_id: string;
  supplier?: Supplier | null;
  status: PurchaseOrderStatus;
  order_date: string;
  expected_delivery_date?: string | null;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  grand_total: number;
  terms?: string | null;
  notes?: string | null;
  created_by_id?: string | null;
  creator_name?: string | null;
  created_at: string;
  updated_at: string;
  items: PurchaseOrderItem[];
}

export interface PurchaseOrderItemCreate {
  item_id: string;
  quantity_ordered: number;
  unit_price: number;
  tax_rate?: number;
  discount_percent?: number;
}

export interface PurchaseOrderCreate {
  supplier_id: string;
  order_date: string;
  expected_delivery_date?: string | null;
  terms?: string | null;
  notes?: string | null;
  items: PurchaseOrderItemCreate[];
}

export interface PurchaseOrderReceiveItem {
  po_item_id: string;
  quantity_to_receive: number;
  batch_number: string;
  expiry_date?: string | null;
}

export interface PurchaseOrderReceive {
  items: PurchaseOrderReceiveItem[];
  notes?: string | null;
}

export interface InventoryDashboardStats {
  total_items: number;
  in_stock_items: number;
  low_stock_items: number;
  out_of_stock_items: number;
  total_valuation: number;
  pending_purchase_orders: number;
  expired_batches_count: number;
  expiring_soon_batches_count: number;
}

export interface InventoryAlerts {
  low_stock_items: InventoryItem[];
  out_of_stock_items: InventoryItem[];
  expiring_batches: InventoryBatch[];
  expired_batches: InventoryBatch[];
  pending_orders_count: number;
}

export interface CategoryValuation {
  category: string;
  item_count: number;
  total_quantity: number;
  valuation: number;
}

export interface StockValuationReport {
  total_valuation: number;
  total_items: number;
  by_category: CategoryValuation[];
}

export interface ProcedureConsumptionItem {
  procedure_name: string;
  consumption_count: number;
  total_cost: number;
}

export interface ProcedureConsumptionReport {
  procedures: ProcedureConsumptionItem[];
  overall_cost: number;
}

export interface MedicineAvailability {
  medicine_name: string;
  status: "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK" | "EXPIRED";
  available_quantity: number;
  unit?: string | null;
  batches_count: number;
  earliest_expiry?: string | null;
}

export interface TreatmentConsumedMaterialItem {
  item_id: string;
  item_name: string;
  item_sku: string;
  quantity: number;
  unit: string;
  unit_cost: number;
  total_cost: number;
  batch_number?: string | null;
}

export interface TreatmentConsumptionResponse {
  treatment_id: string;
  consumed_items: TreatmentConsumedMaterialItem[];
  total_material_cost: number;
  consumed_at: string;
}
